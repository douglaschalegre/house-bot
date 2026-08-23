# Google Sheets failure response 001
Feature: Google Sheets failure response

  Scenario Outline: Google Sheets failure response 001
    Given Google Sheets fails with <provider_error>
    When a user runs <command>
    Then the bot responds with Finance data is temporarily unavailable.
    And the response does not contain <provider_error>
    And the operator log contains <provider_error>

    Examples:
      | command                     | provider_error             |
      | /dindin                     | invalid service credential |
      | /detalhado                  | request quota exceeded     |
      | /historico month:8 year:26  | connection timed out       |
