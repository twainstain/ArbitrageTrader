
package com.hulu.harmony.core.job;

import com.hulu.harmony.api.configuration.ConfigurationKeys;
import com.hulu.harmony.api.configuration.State;
import com.hulu.harmony.api.job.Job;
import com.hulu.harmony.api.job.JobExecutionException;
import com.hulu.harmony.util.JobUtils;
import com.hulu.harmony.util.StateUtils;
import org.apache.log4j.Logger;

/**
 * Base job framework class implementation {@link Job}.
 *
 * @author tamirw
 */
public abstract class BaseJob implements Job<State> {

  private static final Logger LOG = Logger.getLogger(BaseJob.class);

  public BaseJob(State state) {
    StateUtils.validateState(state);
    state.setStartTime(System.currentTimeMillis());
    state.setId(BaseJob.class.getName());
  }

  /**
   * Run phase of a job.
   *
   * @param  state  run phase data and status
   * @throws JobExecutionException in case of post error
   */
  @Override
  public void run(State state)  throws JobExecutionException {
    state.setState(State.RunningState.RUNNING);
    final String phaseName = "run";
    state.setRunningStateStartTime(phaseName, System.currentTimeMillis());
    state.setProp(State.RunningState.RUNNING.toString(), ConfigurationKeys.JOB_STATE_START_STATUS);

    try {
      preExecute(state);
      execute(state);
      postExecute(state);
    } catch (Exception e) {
      JobUtils.setStateEndProperties(state, phaseName, State.RunningState.FAILED.toString());
      throw new JobExecutionException(e);
    }
    JobUtils.setStateEndProperties(state, phaseName, State.RunningState.RUNNING.toString());
  }

  /**
   * ReRun phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobExecutionException in case of re run error
   */
  @Override
  public void reRun(State state)  throws JobExecutionException {
    final String phaseName = "reRun";
    state.setRunningStateStartTime(phaseName, System.currentTimeMillis());
    state.setProp(State.RunningState.RUNNING.toString(), ConfigurationKeys.JOB_STATE_START_STATUS);

    try {
      cleanup(state);
      preExecute(state);
      execute(state);
      postExecute(state);
    } catch (Exception e) {
      JobUtils.setStateEndProperties(state, phaseName, State.RunningState.FAILED.toString());
      throw new JobExecutionException(e);
    }
    JobUtils.setStateEndProperties(state, phaseName, State.RunningState.RUNNING.toString());
  }

}
