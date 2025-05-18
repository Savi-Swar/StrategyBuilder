import random
from treys import Deck, Evaluator, Card

NUM_PLAYERS = 4  # 4 ppls playing

def play_texas_holdem():
    deck = Deck()  # fresh deck, shuffle auto
    evaluator = Evaluator()  # rank hands
    hands = {}  # store player hands

    # deal 2 hole cards to each player
    for i in range(NUM_PLAYERS):
        player = f"Player {i+1}"
        hands[player] = deck.draw(2)  # grab 2 cards

    # flop + turn + river (5 total)
    community_cards = deck.draw(5)

    print("\n🃏 Community Cards:")
    print(Card.print_pretty_cards(community_cards))  # show cards in clean format

    # show each player's hand
    for player, hand in hands.items():
        print(f"{player}: {Card.print_pretty_cards(hand)}")

    print("\n📊 Best Hands:")

    # track best hands
    best_hands = []
    for player, hand in hands.items():
        score = evaluator.evaluate(community_cards, hand)  # eval full hand
        hand_rank = evaluator.get_rank_class(score)  # get category (pair, flush, etc.)
        hand_name = evaluator.class_to_string(hand_rank)  # convert to readable name
        best_hands.append((player, hand_name, score))

    # sort by best hand (lower score = better)
    best_hands.sort(key=lambda x: x[2])

    # print what each player has
    for player, hand_name, _ in best_hands:
        print(f"{player}: {hand_name}")

    # show the winner
    print(f"\n🏆 Winner: {best_hands[0][0]} with {best_hands[0][1]}!")

# run game
if __name__ == "__main__":
    play_texas_holdem()
