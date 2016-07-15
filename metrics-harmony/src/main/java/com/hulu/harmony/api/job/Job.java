
package com.hulu.harmony.api.job;

import com.hulu.harmony.api.management.JobManagement;

/**
 * An interface for job
 *
 * @param <S>  state type
 *
 * @author tamirw
 */
public interface Job<S> extends JobExecution<S> , JobManagement<S> {

}
