
package com.hulu.harmony.api.job;

/**
 * An interface for job execution
 *
 * @param <S>  state type
 *
 * @author tamirw
 */
public interface JobExecution<S> {

  /**
   * Pre Execute phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobExecutionException in case of pre execute error
   */
  void preExecute(S state) throws JobExecutionException;

  /**
   * Execute phase of a job.
   *
   * @param  state  execute phase data and status
   * @throws JobExecutionException in case of execute error
   */
  void execute(S state) throws JobExecutionException;


  /**
   * Post Execute phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobExecutionException in case of post error
   */
  void postExecute(S state) throws JobExecutionException;

  /**
   * Run phase of a job.
   *
   * @param  state  run phase data and status
   * @throws JobExecutionException in case of post error
   */
  void run(S state) throws JobExecutionException;

  /**
   * ReRun phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobExecutionException in case of re run error
   */
  void reRun(S state) throws JobExecutionException;

  /**
   * Cancel job run.
   *
   * @param  state  configuration and runtime data
   * @throws JobExecutionException in case of re run error
   */
  void cancel(S state) throws JobExecutionException;

  /**
   * Job Cleanup.
   *
   * @throws JobExecutionException if there is anything wrong doing job cleanup.
   */
  S cleanup(S state) throws JobExecutionException;

}
