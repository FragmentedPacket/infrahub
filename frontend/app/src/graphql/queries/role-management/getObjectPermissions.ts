import { gql } from "@apollo/client";

export const GET_ROLE_MANAGEMENT_OBJECT_PERMISSIONS = gql`
  query GET_ROLE_MANAGEMENT_OBJECT_PERMISSIONS {
    CoreObjectPermission {
      edges {
        node {
          display_label
          name {
            value
          }
          branch {
            value
          }
          namespace {
            value
          }
          action {
            value
          }
          decision {
            value
          }
          roles {
            count
          }
          identifier {
            value
          }
        }
      }
    }
  }
`;
