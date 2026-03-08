FAQ
===

This page gives an overview of issues that do not lead to an error but to display mistakes, with the fixes belonging to
them.

Colors Are Always White
-----------------------
If a color always appear as white, this usually means you have defined your color using values between 0 and 255, but
squap always uses values between 0 and 1.

Plot Is Flickering
------------------
This flickering can be fixed with :func:`squap.disable_flicker`.
