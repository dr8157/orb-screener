import React from 'react';
import { getScoreClass } from '../../utils/formatters';

/**
 * Premium score badge with gradient and glow effects
 */
const ScoreBadge = ({ score }) => {
    const scoreNum = typeof score === 'number' ? score : parseInt(score) || 0;
    const scoreClass = getScoreClass(scoreNum);

    return (
        <div className={`score-badge ${scoreClass}`}>
            {scoreNum}
        </div>
    );
};

export default ScoreBadge;
