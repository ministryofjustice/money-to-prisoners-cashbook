Feature: History page
  As a user
  I want to be able to see the history page
  So that I can see the list of payments added to NOMIS

  Scenario: Going to the history page
    Given I am signed in
    When I go to the "History" page
    Then I should see "Credit history"
    And I should see a "Search" button
    And I should not see "Payments processed by"

  Scenario: Do a search and make sure it takes you back to the history page
    Given I am signed in
    When I go to the "History" page
    And I click on the "Search" button
    Then I should see "Credit history"
