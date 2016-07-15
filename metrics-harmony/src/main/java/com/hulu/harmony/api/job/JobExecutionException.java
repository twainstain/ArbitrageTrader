
package com.hulu.harmony.api.job;

/**
 * A type of {@link Exception} thrown when there's anything wrong
 * with the job execution.
 *
 * @author tamirw
 */
public class JobExecutionException extends Exception {

  private static final long serialVersionUID = 2L;

  public JobExecutionException(Throwable cause) {
    super(cause);
  }

  public JobExecutionException(String message, Throwable cause) {
    super(message, cause);
  }

  public JobExecutionException(String message) {
    super(message);
  }
}
