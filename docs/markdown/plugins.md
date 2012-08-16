# Plugins

In order to take advantage of the `requires_signature` functionality
available to environments you can create an `RpmSignPlugin`.

You can create your own `RpmSignPlugin` by subclassing the abstract
class `juicer.common.RpmSignPlugin`.

    class RpmSignPlugin(object):

	def sign_rpms(self, rpm_files=None):
	    """sign it however you need to"""
	    raise NotImplementedError

## Example

Here is an example `RpmSignPlugin` without any functionality.

    import juicer.common.RpmSignPlugin

    class RedhatRpmSign(juicer.common.RpmSignPlugin.RpmSignPlugin):

	def sign_rpms(self, rpm_files=None):

	    Here we would do whatever we needed to sign an rpm file
	    using whichever key we require.

In order to make use of this plugin one would need to place it in a
location available to python and add the following to your config
file.

    rpm_sign_plugin: my.path.RpmSignPlugin
