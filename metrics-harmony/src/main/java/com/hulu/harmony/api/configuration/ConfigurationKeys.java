
package com.hulu.harmony.api.configuration;

/**
 * Configuration property keys list.
 */
public class ConfigurationKeys {

  /**
   * Common job configuration properties.
   */
  public static final String JOB_NAME_KEY = "job.name";
  public static final String JOB_TYPE_KEY = "job.type";
  public static final String JOB_GROUP_KEY = "job.group";
  public static final String JOB_DESCRIPTION_KEY = "job.description";
  public static final String JOB_STATE_START_STATUS = "start";
  public static final String JOB_STATE_FINISH_STATUS = "finish";
  public static final String JOB_STATE_START_TIME_KEY_FORMAT = "job.%s.start.time";
  public static final String JOB_STATE_END_TIME_KEY_FORMAT = "job.%s.end.time";
  public static final String JOB_PHASE_STATE_START_TIME_KEY_FORMAT = "job.%s.%s.start.time";
  public static final String JOB_PHASE_STATE_END_TIME_KEY_FORMAT = "job.%s.%s.end.time";
  public static final String JOB_SOURCE_CLASS_KEY = "job.class";



}
