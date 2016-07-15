
package com.hulu.harmony.core.publishing;

import com.hulu.harmony.api.configuration.State;
import com.hulu.harmony.api.job.JobExecutionException;
import com.hulu.harmony.core.job.BaseJob;
import org.apache.avro.Schema;

import java.io.IOException;

/**
 * Base publishing job framework
 *
 * @author tamirw
 */
public abstract class BasePublishingJob extends BaseJob {

  public BasePublishingJob(State state) {
    super(state);
  }
  /**
   * Get schema metadata
   *
   * @param  state  configuration and runtime data
   * @throws JobExecutionException in case of re run error
   */
  public abstract Schema getSchemaMetadata(State state) throws JobExecutionException;

  /**
   * Generate aggregation query
   *
   * @param  state  configuration and runtime data
   * @throws IOException in case of re run error
   */
  public abstract void publishData(State state) throws IOException;

}
