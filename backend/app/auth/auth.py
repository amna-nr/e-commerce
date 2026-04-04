# auth file routes and functions 

# register 
# check if passwords match 
# hash password 
# store username and password in db 

# login 
# check if user exists in db 
# hash password 
# check password in db vs users both hashed 
# if login successful generate access token 
# generate refresh token 
# store refresh token in redis 
# return both tokens 

# refresh 
# check if refresh token exists in redis 
# check if user exists in db
# generate new access token 
# invalidate old refresh token 
# generate new refresh token 
# return both tokens 

