Feature: Signing out
  As a user
  I want to be able to sign out
  So that I do not leave access to my account open

  Scenario: Successful sign out
    Given I am signed in
    When I sign out
    Then I should see "Digital cashbook: Home" as the page title
