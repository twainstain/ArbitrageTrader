
package com.hulu.harmony.util;

import com.google.common.base.Preconditions;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.hulu.harmony.api.configuration.ConfigurationKeys;
import com.hulu.harmony.api.configuration.State;
import java.util.Map;


/**
 * Utility class for dealing with {@link State} objects.
 */
public class StateUtils {

  /**
   * Converts a {@link JsonObject} to a {@link State} object
   *
   * @param jsonObject  json object
   */
  public static State jsonObjectToState(JsonObject jsonObject) {
    State state = new State();
    for (Map.Entry<String, JsonElement> jsonObjectEntry : jsonObject.entrySet()) {
        state.setProp(jsonObjectEntry.getKey(), jsonObjectEntry.getValue().getAsString());
    }
    return state;
  }

  /**
   * Validate state properties
   *
   * @param state  state configuration and runtime data
   */
  public static void validateState(State state) {
    Preconditions.checkNotNull(state);
    Preconditions.checkState(state.contains(ConfigurationKeys.JOB_NAME_KEY));
    Preconditions.checkState(state.contains(ConfigurationKeys.JOB_GROUP_KEY));
    Preconditions.checkState(state.contains(ConfigurationKeys.JOB_SOURCE_CLASS_KEY));
  }
}
