describe("home page", () => {
    beforeEach(() => {
        cy.visit('localhost:3000');
    });

    it("should have at least 2 manuscripts", () => {
        it('should have exactly three <h6> elements', () => {
            cy.get('h6').should('have.length', 3);
        });
    })

    it('the guidelines should be the first manuscript', () => {
        cy.get('h6').first().should('contain.text', 'Guidelines for Drafting Manuscripts');
    });
})
