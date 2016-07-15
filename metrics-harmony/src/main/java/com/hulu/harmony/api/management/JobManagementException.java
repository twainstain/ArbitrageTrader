
package com.hulu.harmony.api.management;

/**
 * A type of {@link Exception} thrown when there's anything wrong
 * with the job management.
 *
 * @author tamirw
 */
public class JobManagementException extends Exception {

  private static final long serialVersionUID = 3L;

  public JobManagementException(Throwable cause) {
    super(cause);
  }

  public JobManagementException(String message, Throwable cause) {
    super(message, cause);
  }

  public JobManagementException(String message) {
    super(message);
  }
}
