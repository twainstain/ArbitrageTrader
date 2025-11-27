
package com.hulu.harmony.api.configuration;

import org.apache.commons.lang.StringUtils;

import java.util.Properties;


/**
 * A configuration and runtime setting class.
 * Implementes a serializable wrapper class that can be persisted for {@link Properties}.
 *
 * @author tamirw
 */
public class State extends Configuration {

  public enum RunningState {
    BUILDING,
    PENDING,
    RUNNING,
    SUCCESS,
    FAILED,
    CANCELLED
  }

  private long startTime = 0;
  private long endTime = 0;
  private long duration = 0;
  private RunningState state = RunningState.PENDING;

  public State() {
    super();
  }

  public State(Properties properties) {
    super();
    this.properties = properties;
  }

  public State(State otherState) {
    super();
    this.properties = otherState.getProperties();
  }

  /**
   * Get job start time.
   *
   * @return job start time
   */
  public long getStartTime() {
    return this.startTime;
  }

  /**
   * Set job start time.
   *
   * @param startTime job start time
   */
  public void setStartTime(long startTime) {
    this.startTime = startTime;
  }

  /**
   * Set job phase start time.
   *
   * @param startTime start time
   * @param phase phase name
   */
  public void setRunningStateStartTime(String phase, long startTime) {
    String key = String.format(ConfigurationKeys.JOB_STATE_START_TIME_KEY_FORMAT, state.toString());
    if(StringUtils.isNotEmpty(phase)) {
      key = String.format(ConfigurationKeys.JOB_PHASE_STATE_START_TIME_KEY_FORMAT, phase, state.toString());
    }
    setProp(key, startTime);
  }

  /**
   * Get job end time.
   *
   * @return job end time
   */
  public long getEndTime() {
    return this.endTime;
  }

  /**
   * Set job end time.
   *
   * @param endTime job end time
   */
  public void setEndTime(long endTime) {
    this.endTime = endTime;
  }

  /**
   * Set job phase end time.
   *
   * @param endTime end time
   * @param phase phase name
   */
  public void setRunningStateEndTime(String phase, long endTime) {
    String key = String.format(ConfigurationKeys.JOB_STATE_END_TIME_KEY_FORMAT, state.toString());
    if(StringUtils.isNotEmpty(phase)) {
      key = String.format(ConfigurationKeys.JOB_PHASE_STATE_END_TIME_KEY_FORMAT, phase, state.toString());
    }
    setProp(key, endTime);
  }

  /**
   * Get job duration in milliseconds.
   *
   * @return job duration in milliseconds
   */
  public long getDuration() {
    return endTime - startTime;
  }

  /**
   * Get job running state of type {@link RunningState}.
   *
   * @return job running state of type {@link RunningState}
   */
  public synchronized RunningState getState() {
    return this.state;
  }

  /**
   * Set job running state of type {@link RunningState}.
   *
   * @param state job running state of type {@link RunningState}
   */
  public synchronized void setState(RunningState state) {
    this.state = state;
  }


}
