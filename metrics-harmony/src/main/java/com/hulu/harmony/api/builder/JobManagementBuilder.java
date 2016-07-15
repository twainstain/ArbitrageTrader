
package com.hulu.harmony.api.builder;

import com.hulu.harmony.api.management.JobManagement;

/**
 * An interface for job management building
 *
 * @param <S> state type
 *
 * @author tamirw
 */
public interface JobManagementBuilder<S> {

  /**
   * Build job instance
   *
   * @param  state  build configuration and runtime data
   * @throws JobBuilderException in case of  error
   */
  JobManagement build(S state) throws JobBuilderException;

}
