@pytest.fixture(scope="session")

def snowpark_session(request):

    """Create Snowpark session for the entire test session"""

    connection_name = request.config.getoption("--snw-connection") or "devdhmat1_owner"

    if connection_name is None:

        raise ValueError(

            "No connection name specified. You must launch the tests with --snw-connection arg. Alternatively use make test"

        )
 
    session = None

    try:

        session = Session.builder.config("connection_name", connection_name).create()

        yield session

    except Exception as e:

        error_message = f"""Can not create the snowpark session. 

Make sure the {connection_name} credentials are available. 

For ex, you can create the following file: $HOME/.config/snowflake/connections.toml 

-------

    [{connection_name}]

    account = "WBIAPMC-PARTNERRE"

    user = "<YOUR_PARTNERRE_EMAIL>"

    database = "<YOUR_DB>"

    schema = "PUBLIC"

    warehouse = "<YOUR_WAREHOUSE>"

    role = "<YOUR_ROLE>"

    authenticator = "externalbrowser"

-----

Note that we use DEVDHMAT1 for now but we will migrate to another db later. 

    """

        raise ValueError(error_message) from e

    finally:

        if session:

            session.close()
 