core.register_service("connecttest", "http", function(applet)
    local response = "LanPartyOnboardingSystem (LPOS)"
    applet:add_header("Content-Length", string.len(response))
    applet:add_header("Content-Type", "text/plain")
    applet:set_status(200)
    applet:start_response()
    applet:send(response)
end)
