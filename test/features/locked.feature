Feature: Locked payments page
  As a user
  I want to be able to see the Locked Payments page
  So that I can see the list of payments that my colleagues are working on

  Scenario: Going to the Locked payments page
    Given I am signed in
    When I go to the "Locked payments" page
    Then I should see "Credits in progress"
    And I should see "Staff name"
    And I should see "Time in progress"
