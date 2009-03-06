## TODO: REDO THESE TESTS
import sys
import unittest
import numpy as N

from theano.tensor.raw_random import *

from theano import tensor

from theano import compile, gof

class T_random_function(unittest.TestCase):
    def test_basic_usage(self):
        rf = RandomFunction(numpy.random.RandomState.uniform, tensor.dvector, -2.0, 2.0)
        assert not rf.inplace
        assert getattr(rf, 'destroy_map', {}) == {}

        rng_R = random_state_type()

        post_r, out = rf(rng_R, (4,))

        assert out.type == tensor.dvector

        f = compile.function([rng_R], out)

        rng_state0 = numpy.random.RandomState(55)

        f_0 = f(rng_state0)
        f_1 = f(rng_state0)

        assert numpy.all(f_0 == f_1)

    def test_inplace_norun(self):
        rf = RandomFunction(numpy.random.RandomState.uniform, tensor.dvector, -2.0, 2.0,
                inplace=True)
        assert rf.inplace
        assert getattr(rf, 'destroy_map', {}) != {}

    def test_args(self):
        """Test that arguments to RandomFunction are honored"""
        rf2 = RandomFunction(numpy.random.RandomState.uniform, tensor.dvector, -2.0, 2.0)
        rf4 = RandomFunction(numpy.random.RandomState.uniform, tensor.dvector, -4.0, 4.0,
                inplace=True)
        rng_R = random_state_type()

        # use make_node to override some of the self.args
        post_r2, out2 = rf2(rng_R, (4,))
        post_r2_4, out2_4 = rf2(rng_R, (4,), -4.0)
        post_r2_4_4, out2_4_4 = rf2(rng_R, (4,), -4.0, 4.0)
        post_r4, out4 = rf4(rng_R, (4,))

        f = compile.function(
                [compile.In(rng_R, value=numpy.random.RandomState(55), update=post_r4, mutable=True)], 
                [out2, out4, out2_4, out2_4_4], 
                accept_inplace=True)

        f2, f4, f2_4, f2_4_4 = f()
        f2b, f4b, f2_4b, f2_4_4b = f()

        assert numpy.allclose(f2*2, f4)
        assert numpy.allclose(f2_4_4, f4)
        assert not numpy.allclose(f4, f4b)

    def test_inplace_optimization(self):
        """Test that arguments to RandomFunction are honored"""
        #inplace = False
        rf2 = RandomFunction(numpy.random.RandomState.uniform, tensor.dvector, -2.0, 2.0)
        rng_R = random_state_type()

        # use make_node to override some of the self.args
        post_r2, out2 = rf2(rng_R, (4,))

        f = compile.function(
                [compile.In(rng_R, 
                    value=numpy.random.RandomState(55),
                    update=post_r2, 
                    mutable=True)], 
                out2,
                mode='FAST_RUN') #DEBUG_MODE can't pass the id-based test below

        # test that the RandomState object stays the same from function call to function call,
        # but that the values returned change from call to call.

        id0 = id(f[rng_R])
        val0 = f()
        assert id0 == id(f[rng_R])
        val1 = f()
        assert id0 == id(f[rng_R])

        assert not numpy.allclose(val0, val1)



class T_test_module(unittest.TestCase):
    def test_state_propagation(self):
        x = tensor.vector()
        rk = RandomKit('rk', 1000)
        f = compile.function([x, (rk, [gof.Container(r = gof.generic, storage = [123], name='bla')])], rk.binomial(tensor.shape(x)))
        print "RK", rk.value
        f['rk'] = 9873456
        print "RK", rk.value
    
        rvals = [f([1,2,3,4,6, 7, 8]) for i in xrange(5)]
        print rvals
        for i in xrange(5-1):
            for j in xrange(i+1, 5):
                assert not N.all(rvals[i] == rvals[j])

    def test_B(self):
        """Test that random numbers change from call to call!
        
        Also, make sure that the seeding strategy doesn't change without failing a test.
        
        Random numbers can't be too random or experiments aren't repeatable.  Email theano-dev
        before updating the `rvals` in this test.
        """
        class B(RModule):
            def __init__(self):
                super(B, self).__init__()
                
                self.x = compile.Member(tensor.dvector())
                self.r = self.random.uniform(tensor.shape(self.x))
                
                self.f = compile.Method([self.x], self.r)
        class E(RModule):
            def __init__(self):
                super(E, self).__init__()
                self.b = B()
                self.f = compile.Method([self.b.x], self.b.r)

        b = E()
        m = b.make()
        
        m.seed(1000)
    #print m.f(N.ones(5))
    #print m.f(N.ones(5))
    #print m.f(N.ones(5))
        rvals = ["0.74802375876 0.872308123517 0.294830748897 0.803123780003 0.6321109955",
                 "0.00168744844365 0.278638315678 0.725436793755 0.7788480779 0.629885140994",
                 "0.545561221664 0.0992011009108 0.847112593242 0.188015424144 0.158046201298",
                 "0.054382248842 0.563459168529 0.192757276954 0.360455221883 0.174805216702",
                 "0.961942907777 0.49657319422 0.0316111492826 0.0915054717012 0.195877184515"]

        for i in xrange(5):
            s = " ".join([str(n) for n in m.f(N.ones(5))])
            print s
            assert s == rvals[i]

if __name__ == '__main__':
    from theano.tests import main
    main("test_raw_random")
