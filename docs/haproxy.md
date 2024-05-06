# HAproxy Configuration

If you like to change your HAproxy configuration, be aware of the following points:

  * the frontend needs to be named `fe_lpos`
    * within the frontend there has to be exactly one `http-request redirect` that uses as it's if statement `is_ms_redirect_url`
