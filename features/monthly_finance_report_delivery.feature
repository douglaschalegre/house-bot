# Monthly finance report delivery 001
# Monthly finance report delivery 002
Feature: Monthly finance report delivery

  Background:
    Given business days are Monday through Friday

  Scenario Outline: Monthly finance report delivery 001
    When the scheduled finance check runs on <date>
    Then the bot requests the sheet named <sheet>
    And the bot sends one report from <sheet> to the finance channel

    Examples:
      | date       | sheet          |
      | 2026-08-07 | Expenses 08/26 |
      | 2026-09-07 | Expenses 09/26 |
      | 2026-10-07 | Expenses 10/26 |

  Scenario Outline: Monthly finance report delivery 002
    When the scheduled finance check runs on <date>
    Then the bot does not request a finance sheet
    And the bot sends no report to the finance channel

    Examples:
      | date       |
      | 2026-08-06 |
      | 2026-08-08 |
      | 2026-09-08 |
