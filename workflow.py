import logging

log = logging.getLogger(__name__)


def next_states(*states, initial=False, final=False):
    """
    Specify routine for method execution, for example in one Workflow:

        @next_states('bar', 'bomb')
        def foo():
            if lucky:
                self.goto('bar')
            else:
                self.goto('bomb')

        def bar():
            print('done')

    

    :param states: see example below
    :param initial: mark specific method as start point,
    Workflow.run() would goto this method first.
    :param final: done or error, there can be many final states.
    """
    # TODO: add check, now method can goto wherever it wants, even
    # those not mentioned in decorator.

    def wrapper(method):
        meta = getattr(method, '_workflow', {'next': []})
        meta['final'] = final
        meta['initial'] = initial
        meta['next'].extend(states)
        method._workflow = meta
        return method

    return wrapper


def final_state(method):
    return next_states(final=True)(method)


class WorkflowException(Exception):
    pass


class _WorkflowDone(WorkflowException):
    pass


class _WorkflowMeta(type):
    """
    Loop over all class methods, find those decorated, add meta info
    to subclass like SpiderWorkflow, including:
    initial state(as start point) and final result(to tell
    workflow is done).
    """

    def __new__(mcs, name, parents, dct):
        cls = super().__new__(mcs, name, parents, dct)
        if parents:
            mcs._load_meta(cls)
        return cls

    @staticmethod
    def _load_meta(cls):
        cls.final_states = []
        cls.states = []
        cls.initial_state = None

        for name, f in cls.__dict__.items():
            if name.startswith('_') or not callable(f):
                continue
            if not hasattr(f, '_workflow'):
                continue
            meta = getattr(f, '_workflow')
            cls.states.append(name)

            # Initial state
            if meta['initial']:
                if cls.initial_state:
                    raise ValueError("More than one initial state: {} {}".format(
                        cls.initial_state, name))
                cls.initial_state = name

            # Final state should not have any next states
            if meta['final']:
                if meta['next']:
                    raise ValueError("Final state cannot have next "
                                     "states: {}".format(name))
                cls.final_states.append(name)


class Workflow(metaclass=_WorkflowMeta):

    initial_state = None
    final_states = ()
    states = ()  # All states
    _state = None  # Current state(use `instance.state`)

    def __init__(self):
        self.seen_states = []

    @property
    def state(self):
        return self._state or self.initial_state

    def goto(self, next_state=None):
        current_state = self._state

        log.debug('transition called: %s -> %s', current_state, next_state)

        if next_state not in self.states:
            raise ValueError("No such state: {}".format(next_state))

        self.seen_states.append(next_state)
        self._state = next_state

        # Call state method
        method = getattr(self, next_state)

        # Execute state with exception handling
        try:
            method()
        except Exception as e:
            if not isinstance(e, _WorkflowDone):
                log.error(e)
                raise

        if self.state in self.final_states:
            # _WorkflowDone Exception will be handled in `run()`
            raise _WorkflowDone()
        else:
            raise ValueError("Didn't reach final state, current state:"
                             " {}".format(self.state))

    def run(self):
        try:
            self.goto(self.initial_state)
        except _WorkflowDone:
            log.debug("Workflow completed: %s", self)
            log.debug("State transitions: %s", ' -> '.join(self.seen_states))

    def __str__(self):
        return "<{} state={}>".format(self.__class__.__name__, self.state)
