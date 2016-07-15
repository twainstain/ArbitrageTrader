
package com.hulu.harmony.api.builder;

import com.hulu.harmony.api.job.Job;

/**
 * An interface for job building
 *
 * @param <S>  state type
 *
 * @author tamirw
 */
public interface JobBuilder<S> {

  /**
   * Build job instance
   *
   * @param  state  build configuration and runtime data
   * @throws JobBuilderException in case of  error
   */
  Job build(S state) throws JobBuilderException;

}
