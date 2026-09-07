# Monthly finance report delivery 001
# Monthly finance report delivery 002
Feature: Monthly finance report delivery

  Scenario Outline: Monthly finance report delivery 001
    When the scheduled finance check runs on <date>
    Then the bot requests the sheet named <sheet>
    And the bot sends one report from <sheet> to the finance channel

    Examples:
      | date       | sheet          |
      | 2026-08-05 | Expenses 08/26 |
      | 2026-09-05 | Expenses 09/26 |
      | 2026-10-05 | Expenses 10/26 |

  Scenario Outline: Monthly finance report delivery 002
    When the scheduled finance check runs on <date>
    Then the bot does not request a finance sheet
    And the bot sends no report to the finance channel

    Examples:
      | date       |
      | 2026-08-04 |
      | 2026-08-06 |
      | 2026-09-06 |
