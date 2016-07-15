package com.hulu.harmony.core.job;

import com.hulu.harmony.api.builder.JobBuilderException;
import com.hulu.harmony.api.configuration.ConfigurationKeys;
import com.hulu.harmony.api.configuration.State;
import com.hulu.harmony.api.job.Job;
import com.hulu.harmony.api.job.JobExecutionException;
import com.hulu.harmony.core.job.builder.BaseBuilder;
import junit.framework.Assert;
import org.junit.Test;

import java.io.*;

public class JobTest {

    @Test
    public void testBaseBuilder() throws IOException, JobBuilderException ,JobExecutionException {
        State state = new State();
        state.setProp(ConfigurationKeys.JOB_NAME_KEY, "BaseTestJob");
        state.setProp(ConfigurationKeys.JOB_GROUP_KEY, "Test");
        state.setProp(ConfigurationKeys.JOB_SOURCE_CLASS_KEY, "com.hulu.harmony.core.job.BaseTestJob");
        BaseBuilder builder = new BaseBuilder();
        Job<State> job = builder.build(state);
        Assert.assertEquals(job.getClass().getSimpleName(),"BaseTestJob");
    }

    @Test
    public void testBaseTestJob() throws IOException, JobBuilderException ,JobExecutionException {
        State state = new State();
        state.setProp(ConfigurationKeys.JOB_NAME_KEY, "BaseTestJob");
        state.setProp(ConfigurationKeys.JOB_GROUP_KEY, "Test");
        state.setProp(ConfigurationKeys.JOB_SOURCE_CLASS_KEY, "com.hulu.harmony.core.job.BaseTestJob");
        BaseBuilder builder = new BaseBuilder();
        Job<State> job = builder.build(state);
        job.execute(state);
        Assert.assertEquals(true , state.contains("execute"));
        State cancelState = job.cleanup(state);
        Assert.assertEquals(true , cancelState.contains("cleanup"));
    }
}
