#! /usr/bin/python26
from allResStr import block1split1
from allResStr import block1split23

import cgi
form = cgi.FieldStorage() # instantiate only once!
block1split1 = form.getfirst('block1split1', block1split1)
block1split23 = form.getfirst('block1split23', block1split23)

# Avoid script injection escaping the user input
block1split1= cgi.escape(block1split1)
block1split23= cgi.escape(block1split23)

print """\
Content-Type: text/html\n
<html><body>
<p>The submitted name was "%s %s"</p>
</body></html>
""" % (block1split1, block1split23)
