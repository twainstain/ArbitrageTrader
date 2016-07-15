
package com.hulu.harmony.api.configuration;

import com.google.common.base.Preconditions;
import com.google.common.base.Splitter;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableSortedSet;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.apache.commons.collections.IteratorUtils;
import org.apache.commons.lang.StringUtils;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.Writable;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;
import java.util.List;
import java.util.Properties;
import java.util.Set;


/**
 * A configuration and runtime setting class.
 * Implementes a serializable wrapper class that can be persisted for {@link Properties}.
 *
 * @author tamirw
 */
public class State implements Writable {

  private static final Splitter LIST_SPLITTER = Splitter.on(",").trimResults().omitEmptyStrings();

  private String id;

  private final Properties properties;
  private final JsonParser jsonParser = new JsonParser();

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
    this.properties = new Properties();
  }

  public State(Properties properties) {
    this.properties = properties;
  }

  public State(State otherState) {
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

  /**
   * Return a copy of the underlying {@link Properties} object.
   *
   * @return A copy of the underlying {@link Properties} object.
   */
  public Properties getProperties() {
    Properties props = new Properties();
    props.putAll(this.properties);
    return props;
  }

  /**
   * Populates this instance with properties of the other instance.
   *
   * @param otherState the other {@link State} instance
   */
  public void addAll(State otherState) {
    addAll(otherState.properties);
  }

  /**
   * Populates this instance with values of a {@link Properties} instance.
   *
   * @param properties a {@link Properties} instance
   */
  public void addAll(Properties properties) {
    this.properties.putAll(properties);
  }

  /**
   * Add properties in a {@link State} instance that are not in the current instance.
   *
   * @param otherState a {@link State} instance
   */
  public void addAllIfNotExist(State otherState) {
    addAllIfNotExist(otherState.properties);
  }

  /**
   * Add properties in a {@link Properties} instance that are not in the current instance.
   *
   * @param properties a {@link Properties} instance
   */
  public void addAllIfNotExist(Properties properties) {
    for (String key : properties.stringPropertyNames()) {
      if (!this.properties.containsKey(key)) {
        this.properties.setProperty(key, properties.getProperty(key));
      }
    }
  }

  /**
   * Set the id used for state persistence and logging.
   *
   * @param id id of this instance
   */
  public void setId(String id) {
    this.id = id;
  }

  /**
   * Get the id of this instance.
   *
   * @return id of this instance
   */
  public String getId() {
    return this.id;
  }

  /**
   * Set a property.
   *
   * <p>
   *   Both key and value are stored as strings.
   * </p>
   *
   * @param key property key
   * @param value property value
   */
  public void setProp(String key, Object value) {
    this.properties.put(key, value.toString());
  }


  /**
   * Get the value of a property.
   *
   * @param key property key
   * @exception  IOException  if an error occurred when reading the property
   * @return value associated with the key as a string or <code>null</code> if the property is not set
   */
  public String getProp(String key) throws IOException {
    String value = this.properties.getProperty(key , null);
    if (value != null ) return value;
    throw new IOException("property " + key +" not found ");
  }


  /**
   * Get the value of a comma separated property as a {@link List} of strings.
   *
   * @param key property key
   * @exception  IOException  if an error occurred when reading the property
   * @return value associated with the key as a {@link List} of strings
   */
  public List<String> getPropAsList(String key) throws IOException {
    return IteratorUtils.toList(LIST_SPLITTER.split(getProp(key)).iterator());
  }


  /**
   * Get the value of a comma separated property as a {@link Set} of strings.
   *
   * @param key property key
   * @exception  IOException  if an error occurred when reading the property
   * @return value associated with the key as a {@link Set} of strings
   */
  public Set<String> getPropAsSet(String key) throws IOException {
    return ImmutableSet.copyOf(LIST_SPLITTER.split(getProp(key)));
  }


  /**
   * Get the value of a property as a case insensitive {@link Set} of strings.
   *
   * @param key property key
   * @exception  IOException  if an error occurred when reading the property
   * @return value associated with the key as a case insensitive {@link Set} of strings
   */
  public Set<String> getPropAsCaseInsensitiveSet(String key) throws IOException {
    return ImmutableSortedSet.copyOf(String.CASE_INSENSITIVE_ORDER, LIST_SPLITTER.split(getProp(key)));
  }

  /**
   * Get the value of a property as an integer.
   *
   * @param key property key
   * @exception  IOException  if an error occurred when reading the property
   * @return long integer value associated with the key
   */
  public int getPropAsInt(String key) throws IOException {
    return Integer.parseInt(getProp(key));
  }

  /**
   * Get the value of a property as a long integer.
   *
   * @param key property key
   * @exception  IOException  if an error occurred when reading the property
   * @return long integer value associated with the key
   */
  public long getPropAsLong(String key) throws IOException {
    return Long.parseLong(getProp(key));
  }

  /**
   * Get the value of a property as a double.
   *
   * @param key property key
   * @exception  IOException  if an error occurred when reading the property
   * @return long integer value associated with the key
   */
  public double getPropAsDouble (String key) throws IOException {
    return Double.parseDouble(getProp(key));
  }

  /**
   * Get the value of a property as a boolean.
   *
   * @param key property key
   * @exception  IOException  if an error occurred when reading the property
   * @return boolean value associated with the key or the default value if the property is not set
   */
  public boolean getPropAsBoolean(String key) throws IOException {
    return Boolean.parseBoolean(getProp(key));
  }

  /**
   * Get the value of a property as a {@link JsonArray}.
   *
   * @param key property key
   * @return {@link JsonArray} value associated with the key
   */
  public JsonArray getPropAsJsonArray(String key) throws IOException {
    JsonElement jsonElement = this.jsonParser.parse(getProp(key));
    Preconditions.checkArgument(jsonElement.isJsonArray(),
        "Value for key " + key + " is malformed, it must be a JsonArray: " + jsonElement);
    return jsonElement.getAsJsonArray();
  }

  /**
   * Remove a property if it exists.
   *
   * @param key property key
   */
  public void removeProp(String key) {
    this.properties.remove(key);
  }


  /**
   * Get the names of all the properties set in a {@link Set}.
   *
   * @return names of all the properties set in a {@link Set}
   */
  public Set<String> getPropertyNames() {
    return this.properties.stringPropertyNames();
  }

  /**
   * Check if a property is set.
   *
   * @param key property key
   * @return <code>true</code> if the property is set or <code>false</code> otherwise
   */
  public boolean contains(String key) {
    return this.properties.getProperty(key) != null;
  }


  @Override
  public void readFields(DataInput in) throws IOException {
    Preconditions.checkNotNull(in);

    Text txt = new Text();
    int numProperties = in.readInt();

    while (numProperties-- > 0) {
      txt.readFields(in);
      String key = txt.toString();
      txt.readFields(in);
      String value = txt.toString();
      this.properties.put(key, value);
    }
  }

  @Override
  public void write(DataOutput out) throws IOException {
    Preconditions.checkNotNull(out);

    Text txt = new Text();
    out.writeInt(this.properties.size());

    for (Object key : this.properties.keySet()) {
      txt.set((String) key);
      txt.write(out);
      txt.set(this.properties.getProperty((String) key));
      txt.write(out);
    }
  }

  @Override
  public String toString() {
    return this.properties.toString();
  }
}
