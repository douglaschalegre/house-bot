# Shopping list Discord delivery 001
# Shopping list Discord delivery 002
Feature: Shopping list Discord delivery

  Background:
    Given Discord accepts messages containing at most 2000 characters

  Scenario Outline: Shopping list Discord delivery 001
    Given the current shopping list has <item_count> distinct items of <item_length> characters each
    When a user runs /lista
    Then the bot sends every item exactly once in insertion order
    And every response message contains at most 2000 characters

    Examples:
      | item_count | item_length |
      | 1          | 10          |
      | 120        | 30          |

  Scenario Outline: Shopping list Discord delivery 002
    Given the sorting service returns <content_length> characters for a nonempty shopping list
    When a user runs /ordenar
    Then the bot sends all sorted content in order
    And every response message contains at most 2000 characters

    Examples:
      | content_length |
      | 100            |
      | 4500           |
