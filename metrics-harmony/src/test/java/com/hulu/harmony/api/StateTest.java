package com.hulu.harmony.api;

import java.io.*;

import com.hulu.harmony.api.configuration.State;
import org.junit.Assert;
import org.junit.Test;

/**
 * Created by tamir.wainstain on 7/14/16.
 */
public class StateTest {

    @Test
    public void testState() throws IOException {
        State state = new State();

        try {
            state.getProp("string");
        }
        catch (IOException e) {
        }

        state.setProp("string", "some string");
        state.setProp("list", "item1,item2");
        state.setProp("long", -1111111111);
        state.setProp("int", Integer.MAX_VALUE);
        state.setProp("double", Double.MAX_VALUE);
        state.setProp("boolean", true);

        Assert.assertEquals(state.getProp("string"), "some string");
        Assert.assertEquals(state.getPropAsList("list").get(0), "item1");
        Assert.assertEquals(state.getPropAsList("list").get(1), "item2");
        Assert.assertEquals(state.getPropAsLong("long"), -1111111111);
        Assert.assertEquals(state.getPropAsInt("int"), Integer.MAX_VALUE);
        Assert.assertEquals(state.getPropAsDouble("double"), Double.MAX_VALUE, 0);
        Assert.assertEquals(state.getPropAsBoolean("boolean"), true);

        state.setProp("string", "some other string");
        state.setProp("list", "item3,item4");
        state.setProp("long", Long.MIN_VALUE);
        state.setProp("int", Integer.MIN_VALUE);
        state.setProp("double", Double.MIN_VALUE);
        state.setProp("boolean", false);

        Assert.assertNotSame(state.getProp("string"), "some string");
        Assert.assertNotSame(state.getPropAsList("list").get(0), "item1");
        Assert.assertNotSame(state.getPropAsList("list").get(1), "item2");
        Assert.assertNotSame(state.getPropAsLong("long"), -1111111111);
        Assert.assertNotSame(state.getPropAsInt("int"), Integer.MAX_VALUE);
        Assert.assertNotSame(state.getPropAsDouble("double"), Double.MAX_VALUE);
        Assert.assertNotSame(state.getPropAsBoolean("boolean"), true);

        Assert.assertEquals(state.getProp("string"), "some other string");
        Assert.assertEquals(state.getPropAsList("list").get(0), "item3");
        Assert.assertEquals(state.getPropAsList("list").get(1), "item4");
        Assert.assertEquals(state.getPropAsLong("long"), Long.MIN_VALUE);
        Assert.assertEquals(state.getPropAsInt("int"), Integer.MIN_VALUE);
        Assert.assertEquals(state.getPropAsDouble("double"), Double.MIN_VALUE, 0);
        Assert.assertEquals(state.getPropAsBoolean("boolean"), false);

        ByteArrayOutputStream byteStream = new ByteArrayOutputStream(1024);
        DataOutputStream out = new DataOutputStream(byteStream);

        state.write(out);

        DataInputStream in = new DataInputStream(new ByteArrayInputStream(byteStream.toByteArray()));

        state = new State();

        state.readFields(in);

        Assert.assertEquals(state.getProp("string"), "some other string");
        Assert.assertEquals(state.getPropAsList("list").get(0), "item3");
        Assert.assertEquals(state.getPropAsList("list").get(1), "item4");
        Assert.assertEquals(state.getPropAsLong("long"), Long.MIN_VALUE);
        Assert.assertEquals(state.getPropAsInt("int"), Integer.MIN_VALUE);
        Assert.assertEquals(state.getPropAsDouble("double"), Double.MIN_VALUE, 0);
        Assert.assertEquals(state.getPropAsBoolean("boolean"), false);

        State state2 = new State();
        state2.addAll(state);

        Assert.assertEquals(state2.getProp("string"), "some other string");
        Assert.assertEquals(state2.getPropAsList("list").get(0), "item3");
        Assert.assertEquals(state2.getPropAsList("list").get(1), "item4");
        Assert.assertEquals(state2.getPropAsLong("long"), Long.MIN_VALUE);
        Assert.assertEquals(state2.getPropAsInt("int"), Integer.MIN_VALUE);
        Assert.assertEquals(state2.getPropAsDouble("double"), Double.MIN_VALUE, 0);
        Assert.assertEquals(state2.getPropAsBoolean("boolean"), false);
    }
}
