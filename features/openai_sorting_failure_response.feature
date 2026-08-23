# OpenAI sorting failure response 001
Feature: OpenAI sorting failure response

  Scenario Outline: OpenAI sorting failure response 001
    Given a nonempty shopping list
    And OpenAI fails with <provider_error>
    When a user runs /ordenar
    Then the bot responds with Shopping list sorting is temporarily unavailable.
    And the response does not contain <provider_error>
    And the operator log contains <provider_error>

    Examples:
      | provider_error         |
      | invalid API credential |
      | request quota exceeded |
