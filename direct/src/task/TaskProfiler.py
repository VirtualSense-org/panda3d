from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm.StatePush import FunctionCall
from direct.showbase.PythonUtil import Averager

class TaskTracker:
    # call it TaskProfiler to avoid confusion for the user
    notify = directNotify.newCategory("TaskProfiler")
    MinSamples = None
    SpikeThreshold = None
    def __init__(self, namePrefix):
        self._namePrefix = namePrefix
        self._durationAverager = Averager('%s-durationAverager' % namePrefix)
        self._avgSession = None
        self._maxNonSpikeSession = None
        if TaskTracker.MinSamples is None:
            # number of samples required before spikes start getting identified
            TaskTracker.MinSamples = config.GetInt('profile-task-spike-min-samples', 30)
            # defines spike as longer than this multiple of avg task duration
            TaskTracker.SpikeThreshold = config.GetFloat('profile-task-spike-threshold', 10.)
    def destroy(self):
        self.flush()
        del self._namePrefix
        del self._durationAverager
    def flush(self):
        self._durationAverager.reset()
        if self._avgSession:
            self._avgSession.release()
        if self._maxNonSpikeSession:
            self._maxNonSpikeSession.release()
        self._avgSession = None
        self._maxNonSpikeSession = None
    def getNamePrefix(self, namePrefix):
        return self._namePrefix
    def _checkSpike(self, session):
        duration = session.getDuration()
        isSpike = False
        # was it long enough to show up on a printout?
        if duration >= .001:
            # do we have enough samples?
            if self.getNumDurationSamples() > self.MinSamples:
                # was this a spike?
                if duration > (self.getAvgDuration() * self.SpikeThreshold):
                    isSpike = True
                    avgSession = self.getAvgSession()
                    maxNSSession = self.getMaxNonSpikeSession()
                    self.notify.info('task CPU spike profile (%s):\n'
                                     '== AVERAGE (%s seconds)\n%s\n'
                                     '== LONGEST NON-SPIKE (%s seconds)\n%s\n'
                                     '== SPIKE (%s seconds)\n%s' % (
                        self._namePrefix,
                        avgSession.getDuration(), avgSession.getResults(),
                        maxNSSession.getDuration(), maxNSSession.getResults(),
                        duration, session.getResults()))
        return isSpike
    def addProfileSession(self, session):
        isSpike = self._checkSpike(session)
        duration = session.getDuration()
        self._durationAverager.addValue(duration)
        if self.getNumDurationSamples() == self.MinSamples:
            # if we just collected enough samples to check for spikes, see if
            # our max 'non-spike' session collected so far counts as a spike
            # and if so, log it
            if self._checkSpike(self._maxNonSpikeSession):
                self._maxNonSpikeSession = self._avgSession

        storeAvg = True
        storeMaxNS = True
        if self._avgSession is not None:
            avgDur = self.getAvgDuration()
            if abs(self._avgSession.getDuration() - avgDur) < abs(duration - avgDur):
                # current avg data is more average than this new sample, keep the data we've
                # already got stored
                storeAvg = False
        if isSpike:
            storeMaxNS = False
        else:
            if (self._maxNonSpikeSession is not None and
                self._maxNonSpikeSession.getDuration() > duration):
                storeMaxNS = False
        if storeAvg:
            if self._avgSession:
                self._avgSession.release()
            session.acquire()
            self._avgSession = session
        if storeMaxNS:
            if self._maxNonSpikeSession:
                self._maxNonSpikeSession.release()
            session.acquire()
            self._maxNonSpikeSession = session
    def getAvgDuration(self):
        return self._durationAverager.getAverage()
    def getNumDurationSamples(self):
        return self._durationAverager.getCount()
    def getAvgSession(self):
        # returns profile session for closest-to-average sample
        return self._avgSession
    def getMaxNonSpikeSession(self):
        # returns profile session for closest-to-average sample
        return self._maxNonSpikeSession
    def log(self):
        if self._avgSession:
            self.notify.info('task CPU profile (%s):\n'
                             '== AVERAGE (%s seconds)\n%s\n'
                             '== LONGEST NON-SPIKE (%s seconds)\n%s' % (
                self._namePrefix,
                self._avgSession.getDuration(),
                self._avgSession.getResults(),
                self._maxNonSpikeSession.getDuration(),
                self._maxNonSpikeSession.getResults(),
                ))
        else:
            self.notify.info('task CPU profile (%s): no data collected' % self._namePrefix)

class TaskProfiler:
    # this does intermittent profiling of tasks running on the system
    # if a task has a spike in execution time, the profile of the spike is logged
    notify = directNotify.newCategory("TaskProfiler")

    def __init__(self):
        self._enableFC = FunctionCall(self._setEnabled, taskMgr.getProfileTasksSV())
        # table of task name pattern to TaskTracker
        self._namePrefix2tracker = {}
        self._task = None

    def destroy(self):
        if taskMgr.getProfileTasks():
            self._setEnabled(False)
        self._enableFC.destroy()
        for tracker in self._namePrefix2tracker.itervalues():
            tracker.destroy()
        del self._namePrefix2tracker
        del self._task

    def logProfiles(self, name=None):
        if name:
            name = name.lower()
        for namePrefix, tracker in self._namePrefix2tracker.iteritems():
            if (name and (name not in namePrefix.lower())):
                continue
            tracker.log()

    def flush(self, name):
        if name:
            name = name.lower()
        # flush stored task profiles
        for namePrefix, tracker in self._namePrefix2tracker.iteritems():
            if (name and (name not in namePrefix.lower())):
                continue
            tracker.flush()

    def _setEnabled(self, enabled):
        if enabled:
            self._taskName = 'profile-tasks-%s' % id(self)
            taskMgr.add(self._doProfileTasks, self._taskName, priority=-200)
        else:
            taskMgr.remove(self._taskName)
            del self._taskName
        
    def _doProfileTasks(self, task=None):
        # gather data from the previous frame
        # set up for the next frame
        if (self._task is not None) and taskMgr._hasProfiledDesignatedTask():
            session = taskMgr._getLastProfileSession()
            # if we couldn't profile, throw this result out
            if session.profileSucceeded():
                namePrefix = self._task.getNamePrefix()
                if namePrefix not in self._namePrefix2tracker:
                    self._namePrefix2tracker[namePrefix] = TaskTracker(namePrefix)
                tracker = self._namePrefix2tracker[namePrefix]
                tracker.addProfileSession(session)

        # set up the next task
        self._task = taskMgr._getRandomTask()
        taskMgr._setProfileTask(self._task)

        return task.cont
