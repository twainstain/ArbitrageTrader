package com.hulu.harmony.core.job.builder;

import com.google.common.base.Preconditions;
import com.hulu.harmony.api.builder.JobBuilderException;
import com.hulu.harmony.api.configuration.ConfigurationKeys;
import com.hulu.harmony.api.configuration.State;
import com.hulu.harmony.api.job.Job;

import java.lang.reflect.Constructor;

/**
 * Reflection Factory builder
 *
 * @author tamirw
 */
public class ReflectionBuilderFactory {

    public static Job<State> newInstance(State state) throws Exception {

        Preconditions.checkNotNull(state);
        String className = state.getProp(ConfigurationKeys.JOB_SOURCE_CLASS_KEY);

        if (className.isEmpty()) {
            throw new JobBuilderException(ConfigurationKeys.JOB_SOURCE_CLASS_KEY + " key is not set") ;
        } else {
            Class<? extends Job<State>> classParam = (Class<? extends Job<State>>) Class.forName(className);
            return newInstance(classParam, state);
        }
    }

    private static Job<State> newInstance(Class<? extends Job<State>> classParam, State state) throws Exception {
        Constructor<? extends Job<State>> constructor = classParam.getConstructor(State.class);
        return constructor.newInstance(state);
    }
}
