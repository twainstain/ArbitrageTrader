package com.hulu.harmony.core.job.builder;

import com.hulu.harmony.api.builder.JobBuilder;
import com.hulu.harmony.api.builder.JobBuilderException;

import com.hulu.harmony.api.configuration.ConfigurationKeys;
import com.hulu.harmony.api.configuration.State;
import com.hulu.harmony.api.job.Job;

/**
 * Base class for job building
 *
 * @author tamirw
 */
public class BaseBuilder implements JobBuilder<State> {

    /**
     * Build job instance
     *
     * @param  state  build phase data and status
     * @throws JobBuilderException in case of  error
     */
    @Override
    public Job build(State state) throws JobBuilderException {
        try {
            state.setState(State.RunningState.BUILDING);
            final String phaseName = "build";
            state.setRunningStateStartTime(phaseName, System.currentTimeMillis());
            state.setProp(State.RunningState.BUILDING.toString(), ConfigurationKeys.JOB_STATE_START_STATUS);
            Job<State> job = ReflectionBuilderFactory.newInstance(state);
            state.setRunningStateEndTime(phaseName, System.currentTimeMillis());
            state.setProp(State.RunningState.BUILDING.toString(), ConfigurationKeys.JOB_STATE_FINISH_STATUS);
            return job;
        } catch (Exception e) {
            throw new JobBuilderException(e);
        }
    }
}
