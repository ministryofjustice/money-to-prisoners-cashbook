Feature: Signing in
  As a user
  I want to be able to sign in
  So that I can access the system

  Scenario: Successful sign in
    Given I am on the "Sign in" page
    When I sign in with "test_prison_1" and "test_prison_1"
    Then I should see "Logged in as test_prison_1"

  Scenario: Unsuccessful sign in
    Given I am on the "Sign in" page
    When I sign in with "doesnt_exist" and "doesnt_exist"
    Then I should see "There was a problem submitting the form"
