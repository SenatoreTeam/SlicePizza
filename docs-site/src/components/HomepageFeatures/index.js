import clsx from 'clsx';
import Heading from '@theme/Heading';
import Translate from '@docusaurus/Translate';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: <Translate id="features.phase.title">Learn by phase</Translate>,
    icon: '🍕',
    description: (
      <Translate id="features.phase.description">
        {"Each phase starts with a request from Zé's Pizzeria and introduces the technology needed to answer it."}
      </Translate>
    ),
  },
  {
    title: <Translate id="features.hands.title">Hands-on</Translate>,
    icon: '🛠️',
    description: (
      <Translate id="features.hands.description">
        Everything runs on your machine: the API, the database and the Docker stack. Follow along and feel the problems before reaching for tools.
      </Translate>
    ),
  },
  {
    title: <Translate id="features.adr.title">Decisions recorded</Translate>,
    icon: '📝',
    description: (
      <Translate id="features.adr.description">
        Architecture Decision Records explain why each important choice was made, so future contributors know the reasoning.
      </Translate>
    ),
  },
];

function Feature({icon, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        {/* Decorative: the heading below already says what the card is about. */}
        <span className={styles.featureIcon} aria-hidden="true">
          {icon}
        </span>
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
