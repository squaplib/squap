Other Update Methods
====================

Using :func`squap.on_refresh` is not the only way to implement updating plots. Each of the following has their uses, so
before starting a new program decide which method fits best, or combine several of them.

Using Box.bind
--------------

When there is no time dependence but there are parameters which are controlled by input boxes, it is more useful to
make use of :meth:`Box.bind <squap.widgets.input_widget.Box>`. A function is then only run when the value of a
parameter changes.


