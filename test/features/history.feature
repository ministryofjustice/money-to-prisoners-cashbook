Feature: History page
  As a user
  I want to be able to see the history page
  So that I can see the list of payments added to NOMIS

  Scenario: Going to the history page
    Given I am signed in
    When I go to the "History" page
    Then I should see "Payment history"
    And I should see "Search"
