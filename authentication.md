site asks aegis to check permissions
we say sure, and send the site a jwt
user on site is redirected to our portal, with a jwt so we can check if it's legit.
they sign in
we check if it's correct
we redirect the user back to the site, and add a jwt
the site trusts us and gives the user access.
they authenticate requests to their own site with us, using the jwt
