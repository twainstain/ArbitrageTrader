
package com.hulu.harmony.core.builder;

import com.hulu.harmony.api.job.Job;

/**
 * An interface for job building
 *
 * @param <C>  configruation data
 *
 * @author tamirw
 */
public interface JobBuilder<C, S> {

  /**
   * Build job instance
   *
   * @param  configuration  build configuration data
   * @throws JobBuilderException in case of  error
   */
  Job build(C configuration) throws JobBuilderException;

}
