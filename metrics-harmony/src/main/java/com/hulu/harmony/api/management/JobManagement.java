
package com.hulu.harmony.api.management;

/**
 * An interface for job management
 *
 * @param <S>  state type
 *
 * @author tamirw
 */
public interface JobManagement<S> {

  /**
   * Pre Execute phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobManagementException in case of pre execute error
   */
  S get(S state) throws JobManagementException;

  /**
   * Pre Execute phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobManagementException in case of pre execute error
   */
  S create(S state) throws JobManagementException;

  /**
   * Execute phase of a job.
   *
   * @param  state  execute phase data and status
   * @throws JobManagementException in case of execute error
   */
  S modify(S state) throws JobManagementException;

  /**
   * Post Execute phase of a job.
   *
   * @param  state  configuration and runtime data
   * @throws JobManagementException in case of post error
   */
  S delete(S state) throws JobManagementException;


}
