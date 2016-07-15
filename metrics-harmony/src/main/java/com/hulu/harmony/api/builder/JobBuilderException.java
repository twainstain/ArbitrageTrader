
package com.hulu.harmony.api.builder;

/**
 * A type of {@link Exception} thrown when there's anything wrong
 * with the job building.
 *
 * @author tamirw
 */
public class JobBuilderException extends Exception {

  private static final long serialVersionUID = 1L;

  public JobBuilderException(Throwable cause) {
    super(cause);
  }

  public JobBuilderException(String message, Throwable cause) {
    super(message, cause);
  }

  public JobBuilderException(String message) {
    super(message);
  }
}
