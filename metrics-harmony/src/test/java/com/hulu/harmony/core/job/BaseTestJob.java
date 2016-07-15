
package com.hulu.harmony.core.job;

import com.hulu.harmony.api.job.JobExecutionException;
import com.hulu.harmony.api.management.JobManagementException;;
import com.hulu.harmony.api.configuration.State;
import com.hulu.harmony.util.JobUtils;
import org.apache.log4j.Logger;

public class BaseTestJob extends BaseJob {

  private static final Logger LOG = Logger.getLogger(BaseTestJob.class);

  public BaseTestJob(State state) { super(state);}

  /**
   * Pre Execute phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobExecutionException in case of pre execute error
   */
  public void preExecute(State state) throws JobExecutionException {
    state.setState(State.RunningState.RUNNING);
    processing(state);
  }

  private void processing(State state) {
    state.setState(State.RunningState.RUNNING);
    final String phaseName = JobUtils.getPhaseName(3);
    LOG.info(String.format("executing phase name -  %s", phaseName));
    state.setProp(phaseName, System.currentTimeMillis());
  }

  /**
   * Execute phase of a job.
   *
   * @param  state  execute phase data and status
   * @throws JobExecutionException in case of execute error
   */
  public void execute(State state) throws JobExecutionException {
    processing(state);
  }

  /**
   * Post Execute phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobExecutionException in case of post error
   */
  public void postExecute(State state) throws JobExecutionException {
    processing(state);
  }

  /**
   * Cancel job run
   *
   * @param  state  configuration and runtime data
   * @throws JobExecutionException in case of re run error
   */
  public void cancel(State state) throws JobExecutionException {
    processing(state);
  }

  /**
   * Job Cleanup .
   *
   * @throws JobExecutionException if there is anything wrong doing job cleanup.
   */
  public State cleanup(State state) throws JobExecutionException {
    processing(state);
    return state;
  }

  /**
   * Pre Execute phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobManagementException in case of pre execute error
   */
  public State get(State state) throws JobManagementException {
    processing(state);
    return state;
  }

  /**
   * Pre Execute phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobManagementException in case of pre execute error
   */
  public State create(State state) throws JobManagementException {
    processing(state);
    return state;
  }

  /**
   * Execute phase of a job.
   *
   * @param  state  execute phase data and status
   * @throws JobManagementException in case of execute error
   */
  public State modify(State state) throws JobManagementException {
    processing(state);
    return state;
  }

  /**
   * Post Execute phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobManagementException in case of post error
   */
  public State delete(State state) throws JobManagementException {
    processing(state);
    return state;
  }

}
