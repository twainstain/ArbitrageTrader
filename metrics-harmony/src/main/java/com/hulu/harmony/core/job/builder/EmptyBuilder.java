package com.hulu.harmony.core.job.builder;

import com.hulu.harmony.api.configuration.State;
import com.hulu.harmony.api.job.Job;

/**
 * Empty builder
 *
 * @author tamirw
 */
public class EmptyBuilder extends BaseBuilder {
    @Override
    public Job build(State state) { return null;}

}