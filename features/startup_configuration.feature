# Startup configuration 001
Feature: Startup configuration

  Scenario Outline: Startup configuration 001
    Given the required startup input <input> is missing
    When the bot starts
    Then the bot exits before connecting to an external service
    And the startup error identifies <input>

    Examples:
      | input            |
      | DISCORD_TOKEN    |
      | OPENAI_API_KEY   |
      | credentials.json |
