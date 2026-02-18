package com.acme.platform.auth;

import java.util.List;

/**
 * Represents a validated user from the Acme auth service.
 */
public class AcmeUser {

    private final String id;
    private final String email;
    private final String teamLabel;
    private List<String> scopes;

    public AcmeUser(String id, String email, String teamLabel) {
        this.id = id;
        this.email = email;
        this.teamLabel = teamLabel;
    }

    public String getId() { return id; }
    public String getEmail() { return email; }
    public String getTeamLabel() { return teamLabel; }
    public List<String> getScopes() { return scopes; }
    public void setScopes(List<String> scopes) { this.scopes = scopes; }
}
