
package com.hulu.harmony.core.aggregation;

import com.hulu.harmony.api.configuration.State;
import com.hulu.harmony.api.job.JobExecutionException;
import com.hulu.harmony.core.job.BaseJob;
import org.apache.avro.Schema;

/**
 * Base aggregation job framework
 *
 * @author tamirw
 */
public abstract class BaseAggregationJob extends BaseJob {

  public BaseAggregationJob(State state) {
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
   * @throws JobExecutionException in case of re run error
   */
  public abstract String generateQuery(State state) throws JobExecutionException;

}
