Feature: New credits
  As a user
  I want to be able to see the credits page
  So that I can see the list of credits to add to NOMIS

  Scenario: Going to the credits page
    Given I am signed in
    When I go to the "New credits" page
    Then I should see "New credits"
    And I should see "Control total"

  Scenario: Submitting payments credited
    Given I am signed in
    When I go to the "New credits" page
    And I click on the first checkbox
    And I click on the "Done" button
    Then I should see "Are you sure?" in a dialog box

  Scenario: Submitting and confirming payments credited
    Given I am signed in
    When I go to the "New credits" page
    And I click on the first checkbox
    And I click on the "Done" button
    And I click on the "Yes" button
    Then I should see "You've credited 1 payment to NOMIS."

  Scenario: Clicking done with no payments credited
    Given I am signed in
    When I go to the "New credits" page
    And I click on the "Done" button
    Then I should see "You have not ticked any credits" in an error box

  Scenario: Printing
    Given I am signed in
    When I go to the "New credits" page
    And I click on the "Print these payments" link
    Then I should see "Do you need to print?" in a dialog box
